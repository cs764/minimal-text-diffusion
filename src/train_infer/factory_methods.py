import sys
sys.path.append('/kaggle/working/minimal-text-diffusion/src')
import modeling.diffusion.gaussian_diffusion as gd
from modeling.diffusion.respace import SpacedDiffusion, space_timesteps
from modeling.predictor.transformer_model import TransformerNetModel


def create_model_and_diffusion(
    class_cond,
    learn_sigma,
    sigma_small,
    num_channels,
    num_heads,
    dropout,
    diffusion_steps,
    noise_schedule,
    timestep_respacing,
    use_kl,
    predict_xstart,
    rescale_timesteps,
    rescale_learned_sigmas,
    use_checkpoint,
    model_arch,
    in_channel,
    out_channel,
    training_mode,
    vocab_size,
    config_name,
    logits_mode,
    init_pretrained,
    freeze_embeddings,
    use_pretrained_embeddings,
    **kwargs,
):
    model = create_model(
        num_channels,
        learn_sigma=learn_sigma,
        class_cond=class_cond,
        use_checkpoint=use_checkpoint,
        num_heads=num_heads,
        dropout=dropout,
        in_channel=in_channel,
        out_channel=out_channel,
        training_mode=training_mode,
        vocab_size=vocab_size,
        config_name=config_name,
        logits_mode=logits_mode,
        init_pretrained=init_pretrained,
        freeze_embeddings=freeze_embeddings,
        use_pretrained_embeddings=use_pretrained_embeddings,
    )
    diffusion = create_gaussian_diffusion(
        steps=diffusion_steps,
        learn_sigma=learn_sigma,
        sigma_small=sigma_small,
        noise_schedule=noise_schedule,
        use_kl=use_kl,
        predict_xstart=predict_xstart,
        rescale_timesteps=rescale_timesteps,
        rescale_learned_sigmas=rescale_learned_sigmas,
        timestep_respacing=timestep_respacing,
        model_arch=model_arch,
        training_mode=training_mode,
    )
    return model, diffusion


def create_model(
    num_channels,
    learn_sigma,
    use_checkpoint,
    class_cond,  # TODO for the next version
    num_heads,
    dropout,
    init_pretrained,
    freeze_embeddings,
    use_pretrained_embeddings,
    in_channel,
    out_channel,
    training_mode,
    vocab_size,
    config_name,
    logits_mode,
):

    return TransformerNetModel(
        in_channels=in_channel,
        model_channels=num_channels,
        out_channels=(out_channel if not learn_sigma else out_channel * 2),
        dropout=dropout,
        use_checkpoint=use_checkpoint,
        num_heads=num_heads,
        config_name=config_name,
        vocab_size=vocab_size,
        logits_mode=logits_mode,
        init_pretrained=init_pretrained,
        use_pretrained_embeddings=use_pretrained_embeddings,
        freeze_embeddings=freeze_embeddings,
        
    )


def create_gaussian_diffusion(
    *,
    steps=1000,
    learn_sigma=False,
    sigma_small=False,
    noise_schedule="linear",
    use_kl=False,
    predict_xstart=False,
    rescale_timesteps=False,
    rescale_learned_sigmas=False,
    timestep_respacing="",
    model_arch="transformer",
    training_mode="diffusion-lm",
):
    betas = gd.get_named_beta_schedule(noise_schedule, steps)

    if use_kl:
        loss_type = gd.LossType.E2E_KL
    else:
        loss_type = gd.LossType.E2E_MSE

    if not timestep_respacing:
        timestep_respacing = [steps]

    # Whether variance is learned or fixed
    model_var_type = None
    if not learn_sigma:
        if sigma_small:
            model_var_type = gd.ModelVarType.FIXED_SMALL
        else:
            model_var_type = gd.ModelVarType.FIXED_LARGE
    else:
        model_var_type = gd.ModelVarType.LEARNED_RANGE

    # what is the interpretation of the output generated by the model? Is it generating the noise or the mean directly?

    model_mean_type = None
    if not predict_xstart:
        model_mean_type = gd.ModelMeanType.EPSILON  # predicts noise
    else:  # predicts starting x (x0 estimate, possibly used by DDIM?)
        model_mean_type = gd.ModelMeanType.START_X

    return SpacedDiffusion(
        use_timesteps=space_timesteps(steps, timestep_respacing),
        betas=betas,
        model_var_type=model_var_type,
        model_mean_type=model_mean_type,
        loss_type=loss_type,
        rescale_timesteps=rescale_timesteps,
        model_arch=model_arch,
        training_mode=training_mode,
    )
